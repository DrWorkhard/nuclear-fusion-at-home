"""Lossless geometry transport controls; no sampling or physical calculation."""

import copy

import numpy as np
import pytest

from fusion_baselines import protected_fine_geometry_codec as codec
from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_arrays, read_json


def fixture(nbase=6, ncoil=256, pattern="mixed"):
    count = 4 * nbase
    shape = (count, ncoil)
    mask = np.zeros(shape, dtype=bool)
    if pattern == "true":
        mask[:] = True
    elif pattern == "mixed":
        mask.ravel()[::3] = True
    pairs = np.array([(i, j) for i in range(count) for j in range(i + 1, count)], dtype=np.int64)
    result = dict(
        parameters=np.arange(ncoil, dtype=float) / ncoil,
        normals=np.ones((count, 3)),
        delta_norms=np.zeros((count, ncoil, 3)),
        speed=np.ones(shape),
        seed_speed=np.ones(shape),
        seed_acceleration=np.ones(shape),
        curvature=np.zeros(shape),
        curvature_available=mask,
        projection=np.zeros(shape),
        lengths=np.ones(count),
        seed_lengths=np.ones(count),
        cp_reference_distances=np.ones(shape),
        cp_reference_indices=np.zeros(shape, dtype=np.int64),
        cp_selected_distances=np.ones(shape),
        cp_selected_indices=np.zeros(shape, dtype=np.int64),
        pairs=pairs,
        pair_distances=np.ones(len(pairs)),
        pair_witnesses=np.zeros(pairs.shape, dtype=np.int64),
    )
    result["projection"].ravel()[0] = -0.0
    return result


def identity(actual, expected):
    assert actual.keys() == expected.keys()
    for key, value in expected.items():
        assert actual[key].dtype == value.dtype
        assert actual[key].shape == value.shape
        assert actual[key].tobytes(order="C") == value.tobytes(order="C")
        assert not np.shares_memory(actual[key], value)


@pytest.mark.parametrize("case", plan.cases(), ids=lambda row: row["label"])
@pytest.mark.parametrize("level", plan.geometry_levels())
@pytest.mark.parametrize("pattern", ["true", "false", "mixed"])
def test_every_class_method_target_level_and_mask_pattern(case, level, pattern):
    raw = fixture(case["nbase"], level["ncoil"], pattern)
    before = copy.deepcopy(raw)
    encoded, descriptor = codec.encode_geometry(raw, case, level)
    assert descriptor == dict(
        codec="protected-geometry-mask-v1", key="curvature_available",
        original_dtype="bool", shape=[4 * case["nbase"], level["ncoil"]],
    )
    identity(raw, before)
    assert encoded["curvature_available"].dtype == np.dtype("uint8")
    assert np.isin(encoded["curvature_available"], [0, 1]).all()
    for key in raw.keys() - {"curvature_available"}:
        identity({key: encoded[key]}, {key: raw[key]})
    decoded = codec.decode_geometry(encoded, descriptor, case, level)
    identity(decoded, raw)
    assert decoded["curvature_available"].dtype == np.dtype(bool)
    assert not np.shares_memory(decoded["curvature_available"], encoded["curvature_available"])


@pytest.mark.parametrize("nbase", [6, 8])
@pytest.mark.parametrize("level", plan.geometry_levels())
def test_canonical_snapshot_roundtrip_keeps_witnesses_and_mask(tmp_path, nbase, level):
    case = next(row for row in plan.cases() if row["nbase"] == nbase)
    raw = fixture(nbase, level["ncoil"])
    encoded, descriptor = codec.encode_geometry(raw, case, level)
    store = SnapshotStore(tmp_path / "raw")
    array_ref = store.arrays("geometry", encoded)
    mask_ref = store.json("geometry-codec", descriptor)
    arrays, metadata = read_arrays(array_ref), read_json(mask_ref)
    identity(arrays, encoded)
    decoded = codec.decode_geometry(arrays, metadata, case, level)
    identity(decoded, raw)
    assert decoded["pairs"].dtype == decoded["pair_witnesses"].dtype == np.dtype("int64")
    assert len(decoded["pairs"]) == (276 if nbase == 6 else 496)


def test_dtype_endianness_empty_scalar_strided_and_signed_zero_preserved(tmp_path):
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    raw = fixture()
    raw.update(
        unsigned=np.array([0, 2**64 - 1], dtype=np.uint64),
        big_endian=np.array([-0.0, 2.0], dtype=">f8"),
        single=np.array([-0.0, np.finfo(np.float32).tiny], dtype=np.float32),
        small_integer=np.arange(8, dtype=np.int8)[::-2],
        fortran=np.asfortranarray(np.arange(12, dtype=float).reshape(3, 4)),
        empty=np.empty((1, 0, 3), dtype=np.int16),
        scalar=np.array(-0.0),
    )
    arrays, descriptor = codec.encode_geometry(raw, case, level)
    store = SnapshotStore(tmp_path / "raw")
    saved = store.arrays("mixed-numeric-types", arrays)
    decoded = codec.decode_geometry(read_arrays(saved), descriptor, case, level)
    identity(decoded, raw)


def test_mutating_either_return_never_mutates_inputs_or_future_outputs():
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    raw = fixture()
    arrays, descriptor = codec.encode_geometry(raw, case, level)
    decoded = codec.decode_geometry(arrays, descriptor, case, level)
    arrays["speed"][0, 0] = 200
    arrays["curvature_available"][0, 0] = 0
    assert raw["speed"][0, 0] == decoded["speed"][0, 0] == 1
    assert bool(raw["curvature_available"][0, 0]) is True
    assert bool(decoded["curvature_available"][0, 0]) is True
    decoded["pair_witnesses"][0, 0] = 3
    assert arrays["pair_witnesses"][0, 0] == raw["pair_witnesses"][0, 0] == 0
    descriptor["shape"][0] = 999
    assert codec.encode_geometry(raw, case, level)[1]["shape"] == [24, 256]


@pytest.mark.parametrize("change", [
    "extra", "missing-codec", "missing-key", "missing-dtype", "missing-shape",
    "codec", "key", "dtype", "shape-nphysical", "shape-ncoil", "shape-bool",
    "shape-float", "shape-tuple", "shape-numpy", "version",
])
def test_descriptor_must_be_exact(change):
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    arrays, descriptor = codec.encode_geometry(fixture(), case, level)
    if change == "extra":
        descriptor["encoded_dtype"] = "uint8"
    elif change.startswith("missing-"):
        del descriptor[{"dtype": "original_dtype"}.get(change[8:], change[8:])]
    elif change == "codec":
        descriptor["codec"] = "protected-geometry-mask-v2"
    elif change == "key":
        descriptor["key"] = "other_mask"
    elif change == "dtype":
        descriptor["original_dtype"] = "uint8"
    elif change == "shape-nphysical":
        descriptor["shape"][0] = 32
    elif change == "shape-ncoil":
        descriptor["shape"][1] = 512
    elif change == "shape-bool":
        descriptor["shape"][0] = True
    elif change == "shape-float":
        descriptor["shape"][0] = 24.0
    elif change == "shape-tuple":
        descriptor["shape"] = (24, 256)
    elif change == "shape-numpy":
        descriptor["shape"][0] = np.int64(24)
    else:
        descriptor["version"] = 1
    with pytest.raises(ValueError, match="descriptor"):
        codec.decode_geometry(arrays, descriptor, case, level)


@pytest.mark.parametrize("descriptor", [None, [], "protected-geometry-mask-v1", {}, True])
def test_missing_or_nonmapping_descriptor_rejected(descriptor):
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    arrays, _ = codec.encode_geometry(fixture(), case, level)
    with pytest.raises(ValueError, match="descriptor"):
        codec.decode_geometry(arrays, descriptor, case, level)


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize("value", [
    None, [], np.ones((24, 256), dtype=float), np.zeros((24, 256), dtype=np.int64),
    np.zeros((24, 256), dtype=np.int8), np.zeros((24, 256), dtype=np.uint16),
    np.zeros((32, 256), dtype=np.uint8), np.zeros((24, 512), dtype=np.uint8),
    np.zeros((24 * 256,), dtype=np.uint8), np.zeros((24, 256, 1), dtype=np.uint8),
])
def test_wrong_mask_type_or_grid_rejected(encoded, value):
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    raw = fixture()
    arrays, descriptor = codec.encode_geometry(raw, case, level)
    chosen = arrays if encoded else raw
    chosen["curvature_available"] = value
    with pytest.raises(ValueError):
        if encoded:
            codec.decode_geometry(chosen, descriptor, case, level)
        else:
            codec.encode_geometry(chosen, case, level)


@pytest.mark.parametrize("invalid", [2, 127, 255])
def test_mask_decode_rejects_nonbinary_uint8(invalid):
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    arrays, descriptor = codec.encode_geometry(fixture(), case, level)
    arrays["curvature_available"][2, 17] = invalid
    with pytest.raises(ValueError, match="binary"):
        codec.decode_geometry(arrays, descriptor, case, level)


def test_mask_encode_requires_bool_and_decode_requires_uint8():
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    raw = fixture()
    arrays, descriptor = codec.encode_geometry(raw, case, level)
    with pytest.raises(ValueError, match="dtype"):
        codec.encode_geometry(arrays, case, level)
    with pytest.raises(ValueError, match="dtype"):
        codec.decode_geometry(raw, descriptor, case, level)


def test_noncanonical_boolean_storage_is_not_silently_normalized():
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    raw = fixture()
    raw["curvature_available"].view(np.uint8)[0, 0] = 2
    with pytest.raises(ValueError, match="boolean"):
        codec.encode_geometry(raw, case, level)


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize("key", ["speed", "curvature_available"])
def test_dtype_metadata_that_numeric_archive_discards_is_rejected(encoded, key):
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    raw = fixture()
    arrays, descriptor = codec.encode_geometry(raw, case, level)
    chosen = arrays if encoded else raw
    old = chosen[key]
    chosen[key] = old.view(np.dtype(old.dtype, metadata={"unrecorded": "value"}))
    with pytest.raises(ValueError, match="metadata"):
        if encoded:
            codec.decode_geometry(chosen, descriptor, case, level)
        else:
            codec.encode_geometry(chosen, case, level)


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize("change", [
    "missing", "none", "empty", "tuple", "bad-key", "integer-key", "list-value",
    "boolean", "complex", "object", "string", "nan", "inf", "many-arrays", "dimensions",
])
def test_other_arrays_not_coerced_and_mappings_bounded(encoded, change):
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    raw = fixture()
    arrays, descriptor = codec.encode_geometry(raw, case, level)
    chosen = arrays if encoded else raw
    if change == "missing":
        del chosen["curvature_available"]
    elif change == "none":
        chosen = None
    elif change == "empty":
        chosen = {}
    elif change == "tuple":
        chosen = tuple(chosen.items())
    elif change == "bad-key":
        chosen["../escape"] = np.zeros(1)
    elif change == "integer-key":
        chosen[3] = np.zeros(1)
    elif change == "many-arrays":
        chosen.update({f"other_{i}": np.zeros(1) for i in range(65)})
    else:
        chosen["other"] = {
            "list-value": [1.0], "boolean": np.zeros(1, dtype=bool),
            "complex": np.zeros(1, dtype=complex), "object": np.zeros(1, dtype=object),
            "string": np.array(["1"]), "nan": np.array([np.nan]), "inf": np.array([np.inf]),
            "dimensions": np.zeros((1,) * 9),
        }[change]
    with pytest.raises(ValueError):
        if encoded:
            codec.decode_geometry(chosen, descriptor, case, level)
        else:
            codec.encode_geometry(chosen, case, level)


def test_bounded_bytes_without_allocating_large_archive(monkeypatch):
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    raw = fixture()
    monkeypatch.setattr(codec, "MAX_BYTES", 1)
    with pytest.raises(ValueError, match="bounded"):
        codec.encode_geometry(raw, case, level)


@pytest.mark.parametrize("change", ["case", "level", "mask-class", "mask-grid"])
def test_case_and_geometry_grid_are_bound(change):
    case, level = plan.cases()[0], plan.geometry_levels()[0]
    arrays, descriptor = codec.encode_geometry(fixture(), case, level)
    if change == "case":
        case["nbase"] = 6.0
    elif change == "level":
        level["offset"] = False
    elif change == "mask-class":
        case = next(row for row in plan.cases() if row["nbase"] == 8)
    else:
        level = plan.geometry_levels()[1]
    with pytest.raises(ValueError):
        codec.decode_geometry(arrays, descriptor, case, level)
