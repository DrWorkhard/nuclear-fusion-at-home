"""Separate sparse interior diagnostic; existing fixed-current reports stay unchanged."""

import math

from .dense import flux_scale, load_input
from .field import field, physical_curves


def vector_rms(actual, target, b2_scale, scale=1.0):
    residual = sum(
        sum((scale * a - b) ** 2 for a, b in zip(got, wanted, strict=True))
        for got, wanted in zip(actual, target, strict=True)
    )
    return math.sqrt(residual / len(target) / b2_scale)


def normalized_interior(candidate, case):
    """Compare currents on the same 64 target points without changing the case.

    Field linearity lets us scale B instead of mutating signed coil currents.
    Flux uses the existing 256-node boundary-loop convention; B uses 512 nodes,
    matching the finer level of the public fixed-current report.
    """
    document = load_input(case)
    scale = flux_scale(candidate, case, document, 256)
    inner = case["groups"]["inner"]
    magnetic = field(inner["points_m"], physical_curves(candidate, case, 512))["B_T"]
    current = max(abs(row["current"]) for row in case["physical"])
    return dict(
        schema_version=1,
        diagnostic="sparse-interior-current-comparison",
        inner_points=len(inner["points_m"]),
        field_coil_nodes=512,
        flux_coil_nodes=256,
        flux_loop_points=256,
        fixed_current_inner_vector_rms=vector_rms(
            magnetic, inner["target_B_T"], case["B2_scale_T2"]
        ),
        flux_normalized_inner_vector_rms=vector_rms(
            magnetic, inner["target_B_T"], case["B2_scale_T2"], scale
        ),
        flux_scale=scale,
        fixed_max_abs_current_A=current,
        flux_normalized_max_abs_current_A=current * scale,
        physical_admission=False,
        step4_pass=False,
        interpretation="Same-kernel diagnostic on 64 bundled interior points, not dense "
        "interior validation, confinement or physical acceptance. Flux scaling preserves "
        "signed current ratios; existing fixed-current reports are unchanged.",
    )
