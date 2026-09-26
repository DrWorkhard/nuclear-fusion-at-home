"""Independent runner fault controls: fresh synthetic inputs only, no saved fields."""

import copy
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import analyze_field_residuals as runner  # noqa: E402


def fixture(monkeypatch, tmp_path):
    clock = [0.0]
    monkeypatch.setattr(runner.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(runner.shutil, "disk_usage", lambda p: SimpleNamespace(free=4 * 1024**3))
    monkeypatch.setattr(runner, "source_identity", lambda root: dict(commit="synthetic-clean"))
    root = tmp_path / "root"
    (root / "evidence").mkdir(parents=True)
    file = root / "evidence/fixed-field-probe-results-v1.json"
    file.touch()
    bound = runner.reference(file)
    monkeypatch.setattr(runner, "RESULT_SHA", bound["sha256"])
    arrays = []
    for boundary_z in (0.2, 0.1):
        value = dict(
            boundary_B=np.tile([1.0, 0.0, boundary_z], (4, 1)),
            boundary_points=np.tile([1.0, 0.0, 0.0], (4, 1)),
            boundary_normals=np.tile([0.0, 0.0, 2.0], (4, 1)),
            boundary_weights=np.ones(4),
        )
        arrays.append(value)
    b2 = 2.0
    metrics = [
        dict(normal_rms=z / math.hypot(1, z), JN=z * z / (2 * b2), boundary_B_rms=math.hypot(1, z))
        for z in (0.2, 0.1)
    ]
    # Runner-only controls deliberately isolate the two numerical implementations;
    # their independent arithmetic qualification belongs to their authors' tests.
    report = dict(metrics=dict(control=metrics[0], proposal=metrics[1]), synthetic=True)
    monkeypatch.setattr(runner.field_residuals, "analyze_pair", lambda *args: copy.deepcopy(report))
    monkeypatch.setattr(
        runner.field_residual_audit, "analyze_pair", lambda *args: copy.deepcopy(report)
    )
    monkeypatch.setattr(
        runner.field_residual_audit,
        "compare",
        lambda a, b: runner.same(a, b, "synthetic comparison"),
    )
    placeholder = root / "synthetic-array-reference.npz"
    placeholder.touch()
    array_ref = runner.reference(placeholder)
    records = []
    for pair in range(2):
        for level in range(4):
            sides = []
            for side in range(2):
                model = dict(
                    level=dict(index=level, nphi=2, ntheta=2, ncoil=256, ninner=32, offset=0),
                    case=dict(label=f"synthetic-n{pair}"),
                    snapshot=dict(B2_scale=b2),
                    arrays=array_ref,
                    state_sha256=("a" if side == 0 else "b") * 64,
                    metrics=metrics[side],
                )
                sides.append(dict(model=model, reference=bound, checked_metrics=metrics[side]))
            records.append(dict(pair_index=pair, level=level, control=sides[0], proposal=sides[1]))
    monkeypatch.setattr(runner, "inputs", lambda result, guard: (copy.deepcopy(records), []))
    loads = []

    def load(ref):
        assert ref == array_ref
        at = len(loads)
        loads.append(at)
        return {k: v.copy() for k, v in arrays[at % 2].items()}

    monkeypatch.setattr(runner, "read_arrays", load)
    return SimpleNamespace(
        root=root,
        output=tmp_path / "output",
        clock=clock,
        loads=loads,
        arrays=arrays,
        loader=load,
        records=records,
    )


def test_synthetic_complete_explicit_return(monkeypatch, tmp_path):
    h = fixture(monkeypatch, tmp_path)
    returned = runner.run(h.root, h.output)
    result = json.loads(Path(returned["path"]).read_bytes())
    assert len(h.loads) == 16 and len(result["comparisons"]) == 8
    assert result["complete"] is True and result["physical_admission"] is False
    assert result["counts"] == dict(
        models=16,
        matched_pairs=8,
        residual_fits=16,
        decompositions=8,
        new_native_requests=0,
        new_gradients=0,
        new_geometry_bounds=0,
    )


def test_late_first_array_prevents_second_load_and_arithmetic(monkeypatch, tmp_path):
    h = fixture(monkeypatch, tmp_path)
    calculations = []
    analyze = runner.field_residuals.analyze_pair

    def load(ref):
        array = h.loader(ref)
        h.clock[0] = 60.0
        return array

    monkeypatch.setattr(runner, "read_arrays", load)
    monkeypatch.setattr(
        runner.field_residuals,
        "analyze_pair",
        lambda *args: calculations.append(1) or analyze(*args),
    )
    with pytest.raises(ValueError):
        runner.run(h.root, h.output)
    assert len(h.loads) == 1 and calculations == []


@pytest.mark.parametrize("shape", [(4, 2), (1, 3), (0, 3)])
def test_matching_but_wrong_boundary_point_shape_is_rejected(monkeypatch, tmp_path, shape):
    h = fixture(monkeypatch, tmp_path)
    for value in h.arrays:
        value["boundary_points"] = np.zeros(shape)
    with pytest.raises(ValueError):
        runner.run(h.root, h.output)


@pytest.mark.parametrize("name", ["pair-0-level-0.json", "result.json"])
def test_short_output_write_cannot_be_returned_as_complete(monkeypatch, tmp_path, name):
    h = fixture(monkeypatch, tmp_path)
    original_open = Path.open

    class ShortWrite:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, value):
            return self.stream.write(value[:-1])

        def __getattr__(self, key):
            return getattr(self.stream, key)

    def open_file(path, mode="r", *args, **kwargs):
        stream = original_open(path, mode, *args, **kwargs)
        return ShortWrite(stream) if mode == "xb" and path.name == name else stream

    monkeypatch.setattr(Path, "open", open_file)
    with pytest.raises((ValueError, OSError)):
        runner.run(h.root, h.output)


def test_pair_boundary_bits_must_match(monkeypatch, tmp_path):
    h = fixture(monkeypatch, tmp_path)
    h.arrays[1]["boundary_normals"][0, 0] = -0.0
    with pytest.raises(ValueError, match="bit-matched"):
        runner.run(h.root, h.output)


@pytest.mark.parametrize("count", [0, 7, 9])
def test_partial_or_extra_intake_cannot_acquire_fixed_completion_counts(
    monkeypatch, tmp_path, count
):
    h = fixture(monkeypatch, tmp_path)
    records = h.records[:count] if count < 8 else h.records + [copy.deepcopy(h.records[-1])]
    monkeypatch.setattr(runner, "inputs", lambda *args: (records, []))
    with pytest.raises(ValueError):
        runner.run(h.root, h.output)
