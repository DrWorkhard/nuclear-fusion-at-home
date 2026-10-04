"""Qualified interior target archives and strict numerical serialization."""

import numpy as np


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    array = np.asarray(value)
    require(array.dtype.kind in "iuf", "real numerical data without coercion required")
    require(array.size > 0 and np.isfinite(array).all(), "nonempty finite numerical data")
    return array.astype(float, copy=False)


def scalar(value):
    array = finite(value)
    require(array.shape == (), "scalar numerical value required")
    return float(array)


def json_value(value):
    """Lossless scalar normalization, never implicit complex/string coercion."""
    if isinstance(value, np.ndarray):
        return json_value(value.tolist())
    if isinstance(value, np.generic):
        converted = value.item()
        require(not isinstance(converted, np.generic), "unsupported extended NumPy scalar")
        return json_value(converted)
    if isinstance(value, dict):
        require(all(type(k) is str for k in value), "JSON string keys required")
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and np.isfinite(value):
        return value
    raise ValueError("nonfinite or unsupported JSON value")


def close(actual, expected, label, rtol=5e-10, atol=1e-12):
    actual, expected = finite(actual), finite(expected)
    require(actual.shape == expected.shape, f"{label}: shape mismatch")
    error = float(abs(actual - expected).max())
    scale = float(abs(expected).max())
    require(error <= atol or error <= rtol * scale, f"{label}: independent mismatch")
    return error


def archived_target(archives64, ninner):
    """Reconstruct from three supplied qualified archives; never read a Wout.

    Each row is {s: .25/.5/.75, n: 64, arrays: {phi,theta,radius,height,
    bt,bp,et,ep,native,...}}. Caller separately binds the immutable references.
    """
    require(type(ninner) is int and ninner in (32, 64), "registered32/64 interior grid")
    require(
        isinstance(archives64, list) and len(archives64) == 3,
        "three qualified64 radial archives required",
    )
    phi, theta = np.meshgrid(
        np.pi * np.arange(64) / 64, 2 * np.pi * np.arange(64) / 64, indexing="ij"
    )
    points, fields, complete = [], [], []
    for row, radius_label in zip(archives64, (0.25, 0.5, 0.75), strict=True):
        require(
            type(row["n"]) is int and row["n"] == 64 and scalar(row["s"]) == radius_label,
            "ordered exact radial and archive grid identity",
        )
        raw = {
            key: finite(row["arrays"][key])
            for key in ("phi", "theta", "radius", "height", "bt", "bp", "et", "ep", "native")
        }
        require(
            all(raw[k].shape == (64, 64) for k in ("phi", "theta", "radius", "height", "bt", "bp"))
            and all(raw[k].shape == (64, 64, 3) for k in ("et", "ep", "native"))
            and np.all(raw["radius"] > 0),
            "qualified archive array shapes and positive R",
        )
        close(raw["phi"], phi, "VMEC toroidal coordinates", rtol=0, atol=5e-12)
        close(raw["theta"], theta, "VMEC poloidal coordinates", rtol=0, atol=5e-12)
        magnetic = raw["bt"][..., None] * raw["et"] + raw["bp"][..., None] * raw["ep"]
        close(raw["native"], magnetic, "archived Cartesian target")
        xyz = np.stack(
            (raw["radius"] * np.cos(raw["phi"]), raw["radius"] * np.sin(raw["phi"]), raw["height"]),
            axis=-1,
        )
        stride = 64 // ninner
        points.append(xyz[::stride, ::stride].reshape(-1, 3))
        fields.append(magnetic[::stride, ::stride].reshape(-1, 3))
        complete.append(magnetic.reshape(-1, 3))
    b2 = float(np.mean(np.sum(np.concatenate(complete) ** 2, axis=1)))
    require(np.isfinite(b2) and b2 > 0, "positive fixed64 target B2 required")
    return dict(
        inner_points=np.concatenate(points),
        inner_target=np.concatenate(fields),
        B2_scale=b2,
        ninner=ninner,
        radii=[0.25, 0.5, 0.75],
        source_resolution=64,
    )
