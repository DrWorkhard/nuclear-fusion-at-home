"""Portable computation/replay reports; never a full scientific acceptance gate."""

import copy
import math

from .data import ROOT, canonical, load_case, require, sha, validate_candidate
from .field import field, metrics, physical_curves, relative_error

SOURCE_NAMES = (
    "src/fusion_public/__init__.py", "src/fusion_public/data.py",
    "src/fusion_public/field.py", "src/fusion_public/report.py",
)
SCOPE = dict(
    fixed_current=True, sampled_fields_only=True, continuous_geometry_checked=False,
    full_surface_checked=False, flux_normalization_checked=False,
    qi_transfer_checked=False, finite_pressure_checked=False,
    robustness_checked=False, physical_admission=False, step4_pass=False,
)


def source_digests():
    return {name: sha((ROOT / name).read_bytes()) for name in SOURCE_NAMES}


def evaluate(candidate, case=None, case_sha=None):
    validate_candidate(candidate)
    if case is None:
        case, case_sha = load_case()
    require(type(case_sha) is str and len(case_sha) == 64, "Bound case digest required")
    levels = []
    for count in (256, 512):
        coils = physical_curves(candidate, case, count)
        fields = {name: field(group["points_m"], coils) for name, group in case["groups"].items()}
        levels.append(dict(ncoil=count, fields=fields, metrics=metrics(fields, case)))
    refinement = {
        name: {quantity: relative_error(levels[0]["fields"][name][quantity],
                                       levels[1]["fields"][name][quantity])
               for quantity in ("B_T", "A_Tm")}
        for name in case["groups"]
    }
    is_reference = canonical(candidate) == canonical(case["seed"])
    reference = None
    if is_reference:
        errors = {
            name: {quantity: relative_error(levels[0]["fields"][name][quantity],
                                           group["native_" + quantity])
                   for quantity in ("B_T", "A_Tm")}
            for name, group in case["groups"].items()
        }
        reference = dict(relative_errors=errors, tolerance=5e-10,
                         passed=all(v <= 5e-10 for row in errors.values() for v in row.values()))
    return dict(
        schema_version=1, kind="public-sampled-field-report", case_id=case["case_id"],
        case_sha256=case_sha, evaluator_sha256=source_digests(),
        candidate=copy.deepcopy(candidate), candidate_sha256=sha(canonical(candidate)),
        scope=SCOPE.copy(), levels=levels, resolution_differences=refinement,
        seed_native_reference=reference,
        interpretation="Sampled fixed-current diagnostics only; no design admission or QI claim",
    )


def _compare(actual, expected, location="report"):
    if isinstance(expected, dict):
        require(type(actual) is dict and set(actual) == set(expected), f"Wrong keys at {location}")
        for key in expected:
            _compare(actual[key], expected[key], f"{location}.{key}")
    elif isinstance(expected, list):
        require(type(actual) is list and len(actual) == len(expected), f"Wrong shape at {location}")
        for i, (a, b) in enumerate(zip(actual, expected, strict=True)):
            _compare(a, b, f"{location}[{i}]")
    elif type(expected) is float:
        require(type(actual) in (int, float) and math.isfinite(actual)
                and math.isclose(actual, expected, rel_tol=5e-10, abs_tol=1e-12),
                f"Numerical replay mismatch at {location}")
    else:
        require(type(actual) is type(expected) and actual == expected, f"Mismatch at {location}")


def audit(document):
    require(type(document) is dict and document.get("kind") == "public-sampled-field-report",
            "Portable field report required")
    case, digest = load_case()
    require(document.get("case_sha256") == digest, "Report belongs to different case bytes")
    require(document.get("evaluator_sha256") == source_digests(),
            "Evaluator changed; use the recorded trusted revision, do not rewrite the old report")
    candidate = validate_candidate(document.get("candidate"))
    require(document.get("candidate_sha256") == sha(canonical(candidate)),
            "Candidate digest changed")
    # No values or pass flags from the submitted report influence recomputation.
    fresh = evaluate(candidate, case, digest)
    _compare(document, fresh)
    return dict(
        schema_version=1, kind="public-report-replay", report_sha256=sha(canonical(document)),
        case_sha256=digest, candidate_sha256=fresh["candidate_sha256"],
        report_replay_pass=True, independent_implementation=False,
        seed_native_reference_pass=(fresh["seed_native_reference"]["passed"]
                                    if fresh["seed_native_reference"] is not None else None),
        physical_admission=False, step4_pass=False,
    )
