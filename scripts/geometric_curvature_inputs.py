"""Immutable ordered field points from the closed geometric direction study."""

import json

import numpy as np
from current_diagnostic_inputs import checked, reference
from geometric_descent_inputs import closed_sources, source_arrays
from run_jac_scaled_study import require_committed

from fusion_baselines.selected_start import mapped_start


def arrays(ref):
    with np.load(checked(ref), allow_pickle=False) as data:
        result = {key: data[key].copy() for key in data.files}
    if not all(np.isfinite(v).all() for v in result.values()):
        raise ValueError("nonfinite curvature source array")
    return result


def frozen_case(row, source):
    original = source_arrays(source)
    doc = json.loads(checked(source["field"]).read_text())
    template = json.loads(checked(row["preparation"]["normalized_start"]).read_text())
    x, permutation, owners = mapped_start(
        doc, template, source["names"], row["names"], original["x"]
    )
    if row["source_indices_in_target_order"] != permutation.tolist() or row["owner_map"] != owners:
        raise ValueError("frozen source physical column mapping changed")
    inverse = np.argsort(permutation)
    events, points, fluxes, steps, directions = row["evaluations"], [], [], [], []
    kinds = ["source"]
    if len(events) != 16 or len(row["directions"]) != 3:
        raise ValueError("exactly sixteen events and three directions per source required")
    for i, (radius, direction) in enumerate(
        zip((1e-6, 1e-5, 1e-4), row["directions"], strict=True)
    ):
        if (
            direction["radius"] != radius
            or not direction["all_pass"]
            or not direction["trial_evaluated"]
            or not direction["gate"]["all_pass"]
        ):
            raise ValueError("closed three-radius native gates and trials required")
        data = arrays(direction["arrays"])
        steps.append(data["step"][inverse])
        directions.append(data["direction"][inverse])
        for eps in (1e-7, 1e-8):
            kinds.extend(f"direction-{i}-eps-{eps}-sign-{sign}" for sign in (1, -1))
        kinds.append(f"direction-{i}-trial")
    for index, (event, kind) in enumerate(zip(events, kinds, strict=True)):
        if event["index"] != index or event["kind"] != kind or event["status"] != "completed":
            raise ValueError("frozen event order/status changed")
        data = arrays(event["arrays"])
        if data["x"].shape != (207,) or data["values"].shape != (138,):
            raise ValueError("complete canonical frozen bundle required")
        if not np.array_equal(data["x"], event["x"]):
            raise ValueError("event point differs from its bundle")
        if index == 0 and (
            not np.array_equal(data["x"], x)
            or np.max(
                abs(data["jacobian"][:, inverse] - original["jacobian"])
                / np.maximum(1, abs(original["jacobian"]))
            )
            > 1e-12
        ):
            raise ValueError("source point/Jacobian replay changed")
        points.append(data["x"][inverse])
        fluxes.append(float(data["values"][0] * 1e-6))
    points, steps, directions = map(np.asarray, (points, steps, directions))
    for i in range(3):
        if np.any(steps[i, original["currents"]] != 0):
            raise ValueError("frozen geometric step changes currents")
        expected = [
            original["x"] + sign * eps * directions[i] for eps in (1e-7, 1e-8) for sign in (1, -1)
        ]
        expected.append(original["x"] + steps[i])
        if not np.array_equal(points[1 + 5 * i : 6 + 5 * i], expected):
            raise ValueError("frozen FD/trial point arithmetic changed")
    return dict(
        points=points,
        fluxes=np.asarray(fluxes),
        steps=steps,
        directions=directions,
        gradient=original["jacobian"][0],
        currents=original["currents"],
        A=arrays(source["arrays"])["A"],
        kinds=kinds,
        bundles=[event["arrays"] for event in events],
    )


def sources(root):
    paths = [
        root / "evidence" / f"geometric-{name}-v1{suffix}.json"
        for name in ("models", "probes")
        for suffix in ("", "-audit")
    ]
    models, model_audit, probes, probe_audit = [json.loads(p.read_text()) for p in paths]
    selected, bindings = closed_sources(root)
    if (
        any(
            r["status"] != "completed" or not r["all_pass"]
            for r in (models, model_audit, probes, probe_audit)
        )
        or model_audit["source"] != reference(paths[0])
        or probes["models"] != reference(paths[0])
        or probes["model_audit"] != reference(paths[1])
        or probe_audit["source"] != reference(paths[2])
        or models["prerequisites"] != bindings
        or [r["source"] for r in probes["cases"]] != selected
        or [r["source"] for r in models["cases"]] != selected
    ):
        raise ValueError("closed source-bound six-model/native-probe studies required")
    for path in paths:
        require_committed(root, path)
    for report in (models, model_audit, probes, probe_audit):
        for ref in report["code"]:
            checked(ref)
    checked(probes["protocol"])
    frozen = []
    for row, source in zip(probes["cases"], selected, strict=True):
        if not row["all_pass"]:
            raise ValueError("both native cases must be qualified")
        for event in row["evaluations"]:
            require_committed(root, checked(event["arrays"]))
        frozen.append(frozen_case(row, source))
    return selected, frozen, [reference(p) for p in paths]
