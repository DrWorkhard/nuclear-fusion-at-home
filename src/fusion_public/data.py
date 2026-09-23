"""Strict portable JSON contracts. No dynamic code, native imports or network."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASE_ID = "clear-coil-samples-v1"
CASE_DIR = ROOT / "examples" / CASE_ID
MAX_JSON_BYTES = 2 * 1024**2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"Nonfinite JSON number: {value}")


def loads(raw):
    require(len(raw) <= MAX_JSON_BYTES, "JSON exceeds 2MiB input limit")
    try:
        document = json.loads(raw, object_pairs_hook=_object, parse_constant=_constant)
    except (RecursionError, UnicodeError) as error:
        raise ValueError("Invalid/deeply nested JSON") from error
    pending, nodes = [(document, 0)], 0
    while pending:
        value, depth = pending.pop()
        nodes += 1
        require(depth <= 32 and nodes <= 100000, "JSON nesting/node limit exceeded")
        if type(value) is dict:
            pending.extend((item, depth+1) for item in value.values())
        elif type(value) is list:
            pending.extend((item, depth+1) for item in value)
        elif type(value) in (int, float):
            number(value)
    return document


def load(path):
    with Path(path).open("rb") as stream:
        return loads(stream.read(MAX_JSON_BYTES + 1))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def save_new(path, value):
    """Exclusive creation: never overwrite an existing report or symlink."""
    path = Path(path)
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(payload)


def number(value):
    require(type(value) in (int, float), "A real JSON number, not a boolean, is required")
    try:
        require(math.isfinite(value), "All numbers must be finite")
    except OverflowError as error:
        raise ValueError("Number exceeds floating-point range") from error
    return float(value)


def vector(value, width=3):
    require(type(value) is list and len(value) == width, f"Exactly {width} components required")
    return [number(v) for v in value]


def parameter_names():
    return [
        f"coil[{i}]/{axis}{kind}({mode})"
        for i in range(6) for axis in "xyz"
        for kind, mode in [("c", 0)] + [(k, m) for m in range(1, 6) for k in ("s", "c")]
    ]


def validate_candidate(candidate):
    require(type(candidate) is dict and set(candidate) == {
        "schema_version", "case_id", "coefficient_unit", "parameter_names", "base_coefficients"
    }, "Exact candidate schema required; put prose/costs in the separate contribution record")
    require(type(candidate["schema_version"]) is int and candidate["schema_version"] == 1,
            "Candidate schema_version must be integer1")
    require(candidate["case_id"] == CASE_ID and candidate["coefficient_unit"] == "m",
            "Registered case and metre-valued coefficients required")
    require(candidate["parameter_names"] == parameter_names(), "Canonical DOF names/order required")
    coils = candidate["base_coefficients"]
    require(type(coils) is list and len(coils) == 6, "Six base coils required")
    for coil in coils:
        require(type(coil) is list and len(coil) == 3, "Three Cartesian axes required")
        for axis in coil:
            require(all(abs(v) <= 10 for v in vector(axis, 11)),
                    "Starter input envelope: each Fourier coefficient must have |c|<=10m")
    return candidate


def load_case(directory=CASE_DIR):
    directory = Path(directory)
    manifest = load(directory / "manifest.json")
    require(type(manifest) is dict and manifest.get("schema_version") == 1
            and type(manifest["schema_version"]) is int and manifest.get("case_id") == CASE_ID,
            "Registered case manifest required")
    require(set(manifest.get("files", {})) == {"case.json", "candidate.json"},
            "Exactly the two fixed relative data files are allowed")
    documents = {}
    for name, expected in manifest["files"].items():
        path = directory / name
        require(not path.is_symlink(), "Case files must not be symbolic links")
        with path.open("rb") as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
        require(sha(raw) == expected, f"Case digest mismatch: {name}")
        documents[name] = loads(raw)
    case = documents["case.json"]
    require(case.get("case_id") == CASE_ID and case.get("schema_version") == 1,
            "Case schema identity")
    validate_candidate(case["seed"])
    require(case["seed"] == documents["candidate.json"], "Seed and template disagree")
    require((case["nbase"], case["order"], case["nfp"]) == (6, 5, 2), "Fixed coil class")
    require(number(case["B2_scale_T2"]) > 0, "Positive frozen target B2 required")
    require(len(case["physical"]) == 24, "All24 physical copies required")
    for index, row in enumerate(case["physical"]):
        require(row["base_index"] == index % 6 and row["period"] == index // 12
                and type(row["flip"]) is bool and row["flip"] == bool(index // 6 % 2),
                "Exact physical-copy order")
        require(type(row["matrix"]) is list and len(row["matrix"]) == 3, "3x3 symmetry matrix")
        for axis in row["matrix"]:
            vector(axis)
        require(number(row["current"]) != 0, "Nonzero frozen physical current")
    require(set(case["groups"]) == {"boundary", "inner", "loop"}, "Three fixed point groups")
    for group in case["groups"].values():
        for key in ("points_m", "native_B_T", "native_A_Tm"):
            require(type(group[key]) is list and len(group[key]) == 64, "Exactly64 sample points")
            for row in group[key]:
                vector(row)
    boundary = case["groups"]["boundary"]
    require(len(boundary["unit_normals"]) == len(boundary["weights"]) == 64,
            "All64 normals/weights")
    for normal, weight in zip(boundary["unit_normals"], boundary["weights"], strict=True):
        require(abs(sum(v*v for v in vector(normal)) - 1) < 1e-10 and number(weight) > 0,
                "Unit normals and positive weights")
    require(len(case["groups"]["inner"]["target_B_T"]) == 64, "All64 target vectors")
    for row in case["groups"]["inner"]["target_B_T"]:
        vector(row)
    return case, manifest["files"]["case.json"]
