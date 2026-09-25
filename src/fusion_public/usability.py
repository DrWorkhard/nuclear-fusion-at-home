"""Human-facing helpers; the source-bound evaluator and report format stay unchanged."""

from copy import deepcopy

from .data import number, parameter_names, validate_candidate
from .field import field, metrics, physical_curves


def validate_for_cli(candidate):
    """Use the original acceptance rules, adding location information on failure."""
    try:
        return validate_candidate(candidate)
    except ValueError as original:
        coils = candidate.get("base_coefficients") if type(candidate) is dict else None
        if type(coils) is list and len(coils) == 6:
            for i, coil in enumerate(coils):
                if type(coil) is not list or len(coil) != 3:
                    message = f"coil[{i}]: exactly 3 Cartesian axes (x, y, z) required"
                    raise ValueError(message) from original
                for axis, values in enumerate(coil):
                    location = f"coil[{i}], axis {'xyz'[axis]}"
                    if type(values) is not list or len(values) != 11:
                        message = f"{location}: exactly 11 Fourier components required"
                        raise ValueError(message) from original
                    for k, value in enumerate(values):
                        name = parameter_names()[33*i + 11*axis + k]
                        try:
                            if abs(number(value)) > 10:
                                raise ValueError("coefficient must have |c| <= 10 m")
                        except ValueError as error:
                            raise ValueError(f"{name} (component {k}): {error}") from original
        raise


def set_coefficient(candidate, name, value):
    """Return a validated copy with exactly one metre-valued coefficient changed."""
    validate_for_cli(candidate)
    names = parameter_names()
    if name not in names:
        raise ValueError(f"Unknown coefficient {name!r}; use a name from parameter_names")
    coil, remainder = divmod(names.index(name), 33)
    axis, component = divmod(remainder, 11)
    result = deepcopy(candidate)
    result["base_coefficients"][coil][axis][component] = number(value)
    return validate_for_cli(result)


def reference_metrics(case):
    """Score the reference with the same 512-node public arithmetic as candidates.

    This is a small public field calculation, not an independent native check.
    Search callers may compute it once; no mutable global case cache is retained.
    """
    coils = physical_curves(case["seed"], case, 512)
    return metrics({name: field(group["points_m"], coils)
                    for name, group in case["groups"].items()}, case)


def score_comparison(report, case):
    """Like-for-like UI comparison; saved reports/native-reference checks are unchanged."""
    reference = reference_metrics(case)
    candidate = report["levels"][1]["metrics"]
    scores = {}
    for name in ("sampled_normal_rms", "sampled_inner_vector_rms"):
        change = candidate[name] - reference[name]
        scores[name] = dict(reference=reference[name], candidate=candidate[name],
                            change=change, change_percent=100 * change / reference[name])
    return dict(
        scores=scores,
        direction="Lower is better for both; negative change is improvement. Report trade-offs.",
        reference_scope="Reference and candidate use the public evaluator at 512 nodes.",
        research_limits=dict(full_grid_normal_rms=1e-4, full_grid_inner_vector_rms=0.01),
        interpretation="Research limits belong to a different full-grid, flux-normalized "
        "profile, not a public pass/fail test. Tiny changes may be numerical noise. "
        "Exploratory lower-score PRs are welcome; this is not proof of a feasible design.",
    )
