"""Verify archive bytes, replay saved field metrics and independently sampled B/A."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/"src"))
sys.path.insert(0, str(HERE))

from summarize import summarize  # noqa: E402

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines.boundary_control_metrics import boundary_metrics  # noqa: E402
from fusion_baselines.realized_field import summarize as summarize_lines  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def close(actual, expected):
    assert np.isfinite(actual).all() and np.isfinite(expected).all()
    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-14)


def replay(manifest_sha):
    assert digest(HERE/"manifest.json") == manifest_sha, "manifest differs from tag annotation"
    manifest = read(HERE/"manifest.json")
    for name, expected in manifest.items():
        path = (HERE/name).resolve()
        assert path.is_relative_to(HERE) and digest(path) == expected, name
    study = read(HERE/"run/study.json")
    original_root = Path(study["provenance"]["repository"]["path"])
    source_count = 0
    for name, expected in study["sources_before"].items():
        path = Path(name)
        if path.is_relative_to(original_root):
            assert digest(ROOT/path.relative_to(original_root)) == expected, name
            source_count += 1
    assert summarize(HERE) == read(HERE/"summary.json"), "derived summary differs"
    original = read(HERE/"original-snapshot.json")
    control, probe = (read(HERE/"run"/arm/"fit/seed.json") for arm in ("C", "P"))
    assert control == original
    excluded = {"order", "names", "base_coefficients"}
    assert {k: v for k, v in control.items() if k not in excluded} == {
        k: v for k, v in probe.items() if k not in excluded}
    assert control["order"] == 5 and probe["order"] == 8
    for a, b in zip(control["base_coefficients"], probe["base_coefficients"], strict=True):
        for x, y in zip(a, b, strict=True):
            assert x == y[:11] and y[11:] == [0.]*6
    check.snapshot_identity(control)
    check.snapshot_identity(probe)
    for arm in ("C", "P"):
        path = HERE/"run"/arm
        report = read(path/"fit/result.json")
        snapshot = read(path/"fit/selected-snapshot.json")
        for row in report["fine"]:
            arrays_path = path/"fit"/f"fine-{row['shift']}.npz"
            assert digest(arrays_path) == row["arrays_sha256"]
            with np.load(arrays_path, allow_pickle=False) as a:
                metrics = boundary_metrics(a["B"].reshape(a["normals"].shape), a["normals"])
                for name, value in metrics.items():
                    close(value, row["metrics"][name])
                close(np.mean(np.sum(a["A"]*a["loop_tangent"], axis=1)),
                      row["metrics"]["measured_flux"])
                points = np.concatenate((a["points"][a["B_indices"]],
                                         a["loop_points"][a["A_indices"]]))
                B, A = check.independent.filament_field_and_potential(
                    points, a["positions"], a["tangents"], a["currents"])
                close(B[:64], a["independent_B"])
                close(A[64:], a["independent_A"])
                close(B[:64], a["B"][a["B_indices"]])
                close(A[64:], a["A"][a["A_indices"]])
        for index, row in enumerate(report["interior"]):
            arrays_path = path/"fit/interior"/f"level-{index}.npz"
            assert digest(arrays_path) == row["arrays_sha256"]
            with np.load(arrays_path, allow_pickle=False) as a:
                metrics = check.field_metrics(a["inner_B"], a["inner_target"], a["loop_A"],
                                               a["loop_tangent"], snapshot, row["ninner"])
                for name, value in metrics.items():
                    close(value, row["metrics"][name])
                points = np.concatenate((a["inner_points"][a["B_indices"]],
                                         a["loop_points"][a["A_indices"]]))
                B, A = check.independent.filament_field_and_potential(
                    points, a["positions"], a["tangents"], a["currents"])
                n = len(a["B_indices"])
                close(B[:n], a["independent_B"])
                close(A[n:], a["independent_A"])
                close(B[:n], a["inner_B"][a["B_indices"]])
                close(A[n:], a["loop_A"][a["A_indices"]])
        trace = read(path/"trace/result.json")
        assert summarize_lines(trace["lines"], 200) == trace["summary"]
        print(arm, "saved field metrics, sampled independent B/A and line summary reproduced")
    print(len(manifest), "archive hashes and", source_count, "producer source hashes verified")
    print("No optimization, tracing, geometry reconstruction or physical acceptance replayed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-sha", required=True,
                        help="SHA256 from immutable tag annotation")
    replay(parser.parse_args().manifest_sha)
