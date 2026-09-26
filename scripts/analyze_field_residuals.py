"""Fixed, saved-array-only residual diagnosis. Never constructs native fields."""

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from fusion_baselines import field_residual_audit, field_residuals
from fusion_baselines.protected_run_snapshots import read_arrays

ROOT = Path(__file__).resolve().parents[1]
RESULT_SHA = "94835d9c3f59552fb2e194d877f1728b2413ba64166ff29453e11e2f05027496"
STUDY_SHA = "7d881cb3a7cc2f58feca4020e9f32f3430fffba0f7eb0cf285c7a0f5f4f906c2"
PROTOCOL_SHA = "ac615306e3723e8346726a91d071eee4e45a51c28a5cb2ec074782786181324d"
JSON_LIMIT = 8 * 1024**2
SCOPE = dict(
    field_pass=False,
    physical_admission=False,
    step4_pass=False,
    ms1_reached=False,
    sota_advance=False,
    physical_extrapolation=False,
)
SOURCES = (
    "scripts/analyze_field_residuals.py",
    "src/fusion_baselines/field_residuals.py",
    "src/fusion_baselines/field_residual_audit.py",
    "src/fusion_baselines/protected_run_snapshots.py",
    "src/fusion_baselines/protected_search_journal.py",
    "docs/optimization/FIELD_RESIDUAL_PROTOCOL.md",
    "pyproject.toml",
    "uv.lock",
)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def encode(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def reference(path):
    path = Path(path).absolute()
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while block := stream.read(1024**2):
            digest.update(block)
            size += len(block)
    return dict(path=str(path), bytes=size, sha256=digest.hexdigest())


def read(reference_value, references, guard):
    guard()
    need(
        type(reference_value) is dict and set(reference_value) == {"path", "bytes", "sha256"},
        "exact registered reference",
    )
    path = Path(reference_value["path"])
    need(path.is_absolute() and path.is_file() and not path.is_symlink(), "regular absolute input")
    size = reference_value["bytes"]
    need(type(size) is int and 0 < size <= JSON_LIMIT, "bounded JSON input")
    with path.open("rb") as stream:
        raw = stream.read(JSON_LIMIT + 1)
    need(
        len(raw) == size and hashlib.sha256(raw).hexdigest() == reference_value["sha256"],
        "registered JSON bytes changed",
    )
    guard()
    value = json.loads(
        raw,
        object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
    )
    encode(value)  # Reject nonfinite numbers, including exponent overflow.
    references.append(reference_value)
    return value


def same(actual, expected, label):
    need(encode(actual) == encode(expected), label)


def inputs(result_reference, guard):
    """Resolve sixteen explicit model records; no arrays or numerical kernels."""
    refs = []
    result = read(result_reference, refs, guard)
    need(
        result["status"] == "completed" and result["sources_unchanged"] is True,
        "completed unchanged prior study",
    )
    same(result["references"]["study"]["sha256"], STUDY_SHA, "fixed returned study")
    study = read(result["references"]["study"], refs, guard)
    manifest = read(result["references"]["inputs"], refs, guard)
    review = read(result["references"]["independent_saved_review"], refs, guard)
    need(review["all_scoped_checks_pass"] is True, "completed prior saved-data review")
    same(review["study"], result["references"]["study"], "same reviewed study")
    need(
        len(study["pairs"]) == 2 and len(manifest["states"]) == 4 and len(result["states"]) == 4,
        "fixed two pairs and four states",
    )
    records = []
    for pair_index, pair in enumerate(study["pairs"]):
        same(pair["pair_index"], pair_index, "fixed pair order")
        for phase in ("producer", "audit"):
            need(pair[phase]["complete"] is True, "explicit completed phase")
        producer = read(pair["producer"]["result"], refs, guard)
        audit = read(pair["audit"]["result"], refs, guard)
        need(
            len(producer["result"]["states"]) == len(audit["result"]["states"]) == 2,
            "two ordered states per pair",
        )
        models = []
        for role in range(2):
            state_index = 2 * pair_index + role
            selected = manifest["states"][state_index]
            archived = result["states"][state_index]
            checked = read(audit["result"]["states"][role], refs, guard)
            need(
                checked["numerical_pass"] is True and checked["complete"] is True,
                "completed numerical qualification",
            )
            same(checked["state_sha256"], selected["state_sha256"], "audited named state")
            same(archived["state_sha256"], selected["state_sha256"], "result named state")
            construction = producer["result"]["states"][role]
            same(construction["state"], state_index, "global state index")
            need(
                len(construction["models"]) == len(checked["models"]) == 6,
                "six original levels, no input subset",
            )
            rows = []
            for level in range(4):
                ref = construction["models"][level]
                model = read(ref, refs, guard)
                same(model["state"], state_index, "model state index")
                for key in ("state_sha256", "names", "x", "case"):
                    same(model[key], selected[key], "model registered " + key)
                    same(model[key], checked["models"][level][key], "audited model " + key)
                same(model["level"], checked["models"][level]["level"], "audited grid")
                same(model["level"]["index"], level, "fixed grid order")
                same(model["snapshot"], checked["models"][level]["snapshot"], "audited snapshot")
                same(model["level"], archived["levels"][level]["level"], "result grid")
                rows.append(
                    dict(
                        reference=ref,
                        model=model,
                        checked_metrics=checked["models"][level]["metrics"],
                    )
                )
            models.append(rows)
        for level in range(4):
            control, proposal = models[0][level], models[1][level]
            same(control["model"]["level"], proposal["model"]["level"], "matched grid")
            for key in ("sources", "seed_geometry", "B2_scale", "target_flux", "names"):
                same(
                    control["model"]["snapshot"][key],
                    proposal["model"]["snapshot"][key],
                    "matched original snapshot " + key,
                )
            records.append(
                dict(pair_index=pair_index, level=level, control=control, proposal=proposal)
            )
    return records, refs


def close(actual, expected, label):
    need(
        math.isfinite(actual)
        and math.isfinite(expected)
        and (abs(actual - expected) <= 1e-12 or abs(actual - expected) <= 5e-10 * abs(expected)),
        label,
    )


def source_identity(root):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    need(not git("status", "--porcelain"), "clean committed source required")
    refs = [reference(root / path) for path in SOURCES]
    same(
        next(r for r in refs if r["path"].endswith("FIELD_RESIDUAL_PROTOCOL.md"))["sha256"],
        PROTOCOL_SHA,
        "unchanged registered protocol",
    )
    return dict(
        commit=git("rev-parse", "HEAD"),
        sources=refs,
        python=sys.version,
        numpy=np.__version__,
        executable=reference(Path(sys.executable).resolve()),
        numpy_init=reference(np.__file__),
    )


def run(root, output):
    started = time.monotonic()
    need(shutil.disk_usage(root).free >= 3 * 1024**3, "3 GiB starting reserve")
    before = source_identity(root)
    output.mkdir(parents=True, exist_ok=False)
    refs, rows = [], []
    charged = 0

    def guard():
        need(time.monotonic() - started < 60, "60 s diagnostic deadline")
        need(shutil.disk_usage(output).free >= 2 * 1024**3, "2 GiB live reserve")

    def publish(name, value):
        nonlocal charged
        guard()
        raw = encode(value)
        charged += len(raw)
        need(charged <= JSON_LIMIT, "8 MiB total output limit")
        path = output / name
        with path.open("xb") as stream:
            need(stream.write(raw) == len(raw), "complete result write required")
            stream.flush()
            os.fsync(stream.fileno())
        guard()
        ref = reference(path)
        need(
            ref["bytes"] == len(raw) and ref["sha256"] == hashlib.sha256(raw).hexdigest(),
            "exact published result bytes",
        )
        guard()
        return ref

    try:
        result_ref = reference(root / "evidence/fixed-field-probe-results-v1.json")
        same(result_ref["sha256"], RESULT_SHA, "fixed completed result bytes")
        records, refs = inputs(result_ref, guard)
        same(
            [(row["pair_index"], row["level"]) for row in records],
            [(pair, level) for pair in range(2) for level in range(4)],
            "exact eight-comparison schedule",
        )
        for record in records:
            guard()
            control, proposal = record["control"], record["proposal"]
            a = read_arrays(control["model"]["arrays"])
            guard()
            b = read_arrays(proposal["model"]["arrays"])
            guard()
            refs.extend(row["model"]["arrays"] for row in (control, proposal))
            expected_count = control["model"]["level"]["nphi"] * control["model"]["level"]["ntheta"]
            need(
                a["boundary_B"].shape == b["boundary_B"].shape == (expected_count, 3),
                "complete registered boundary arrays",
            )
            for key in ("boundary_points", "boundary_normals", "boundary_weights"):
                shape = (expected_count,) if key == "boundary_weights" else (expected_count, 3)
                need(a[key].shape == b[key].shape == shape, "complete boundary " + key)
                need(
                    a[key].shape == b[key].shape
                    and a[key].dtype == b[key].dtype
                    and a[key].tobytes() == b[key].tobytes(),
                    "bit-matched boundary " + key,
                )
            arguments = (
                a["boundary_B"],
                b["boundary_B"],
                a["boundary_normals"],
                a["boundary_weights"],
                control["model"]["snapshot"]["B2_scale"],
            )
            guard()
            derived = field_residuals.analyze_pair(*arguments)
            guard()
            independent = field_residual_audit.analyze_pair(*arguments)
            field_residual_audit.compare(derived, independent)
            for label, original in (("control", control), ("proposal", proposal)):
                for key in ("normal_rms", "JN", "boundary_B_rms"):
                    close(
                        derived["metrics"][label][key],
                        original["model"]["metrics"][key],
                        "producer metric reconstruction " + label + " " + key,
                    )
                    close(
                        derived["metrics"][label][key],
                        original["checked_metrics"][key],
                        "audited metric reconstruction " + label + " " + key,
                    )
            row = dict(
                pair_index=record["pair_index"],
                level=control["model"]["level"],
                case=control["model"]["case"],
                control={key: control["model"][key] for key in ("state_sha256", "arrays")},
                proposal={key: proposal["model"][key] for key in ("state_sha256", "arrays")},
                model_references=[control["reference"], proposal["reference"]],
                producer=derived,
                independent=independent,
                independently_checked=True,
                **SCOPE,
            )
            rows.append(publish(f"pair-{record['pair_index']}-level-{record['level']}.json", row))
            del a, b, arguments
        guard()
        for ref in refs:
            guard()
            same(reference(ref["path"]), ref, "input unchanged after analysis")
        after = source_identity(root)
        same(after, before, "source unchanged during analysis")
        need(len(rows) == 8, "complete comparison coverage")
        result = dict(
            schema_version=1,
            kind="saved-field-residual-diagnosis",
            complete=True,
            sources_before=before,
            sources_after=after,
            inputs=refs,
            comparisons=rows,
            counts=dict(
                models=16,
                matched_pairs=8,
                residual_fits=16,
                decompositions=8,
                new_native_requests=0,
                new_gradients=0,
                new_geometry_bounds=0,
            ),
            elapsed_seconds=time.monotonic() - started,
            scientific_bytes_before_result=charged,
            **SCOPE,
        )
        ref = publish("result.json", result)
        guard()
        return ref
    except BaseException as error:
        # Failure publication is never a positive returned result; retain partial rows.
        raw = encode(dict(complete=False, error=repr(error), comparisons=rows, **SCOPE))
        if charged + len(raw) <= JSON_LIMIT:
            with (output / "failure.json").open("xb") as stream:
                need(stream.write(raw) == len(raw), "complete failure write required")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(run(ROOT, arguments.output.absolute()), sort_keys=True))


if __name__ == "__main__":
    main()
